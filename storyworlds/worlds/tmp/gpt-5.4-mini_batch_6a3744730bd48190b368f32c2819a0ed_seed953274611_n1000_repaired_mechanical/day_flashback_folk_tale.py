#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/day_flashback_folk_tale.py
===========================================================

A tiny standalone storyworld in a folk-tale style, centered on a single day and
a flashback that explains why the day's trouble matters.

Premise
-------
A child or small villager spends the day trying to finish a simple task before
nightfall. Something in the present becomes harder because of a remembered past
promise, gift, or warning. The flashback reveals why the helper tool, token, or
habit matters. The ending shows a concrete change in the world: the task is
done, the promise is kept, or the lost thing is found again.

This world keeps the setting small, concrete, and child-facing:
- a village path, cottage, field, or wood-edge
- a helpful object with a practical use
- a remembered moment from an earlier day
- a folk-tale tone with plain, warm language

The story is built from world state rather than swapped nouns: the same day can
turn hopeful, tricky, or tender depending on the chosen object, task, and memory.
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    weather: str
    dusk_image: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Task:
    id: str
    title: str
    verb: str
    goal: str
    risk: str
    requires: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Memory:
    id: str
    title: str
    ago: str
    lesson: str
    object_name: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Aid:
    id: str
    label: str
    use: str
    glow: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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
        import copy as _copy
        c = World()
        c.entities = _copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


SETTINGS = {
    "village": Setting(id="village", place="the little village lane", weather="golden", dusk_image="the roof tops went gold at sunset"),
    "field": Setting(id="field", place="the open field behind the cottages", weather="windy", dusk_image="the grass bowed like green waves"),
    "wood": Setting(id="wood", place="the edge of the old wood", weather="cool", dusk_image="the trees turned dark and tall"),
}

TASKS = {
    "fetch_water": Task(id="fetch_water", title="carry water home", verb="carry the water pail home", goal="the house before supper", risk="spilling the pail in the rush", requires="water_pail", tags={"water", "journey"}),
    "mend_rope": Task(id="mend_rope", title="mend the rope fence", verb="fix the rope fence", goal="the gate before night", risk="the broken rope letting the animals wander", requires="rope", tags={"rope", "repair"}),
    "find_bell": Task(id="find_bell", title="find the lost bell", verb="find the lost bell", goal="the old oak", risk="the bell being too hard to hear at dusk", requires="bell", tags={"bell", "search"}),
}

MEMORIES = {
    "storm": Memory(id="storm", title="the storm flashback", ago="two days ago", lesson="the old path was safe only with a lamp", object_name="lantern", tags={"storm", "lamp"}),
    "promise": Memory(id="promise", title="the promise flashback", ago="last winter", lesson="a promise should be kept even when the day grows long", object_name="ribbon", tags={"promise", "ribbon"}),
    "grandmother": Memory(id="grandmother", title="the grandmother flashback", ago="many summers ago", lesson="small helpers can do big good when they stay calm", object_name="bell", tags={"grandmother", "bell"}),
}

AIDS = {
    "lantern": Aid(id="lantern", label="lantern", use="carry it home to light the path", glow="glowed like a tiny moon", tags={"lamp"}),
    "needle": Aid(id="needle", label="needle and thread", use="stitch the rope together", glow="flashed silver in the hand", tags={"rope"}),
    "string": Aid(id="string", label="bright string", use="tie the bell to a stick and shake it loose", glow="shone red as berries", tags={"bell"}),
}

GIRL_NAMES = ["Mara", "Nell", "Tia", "Rin", "Elsa"]
BOY_NAMES = ["Pip", "Jory", "Bram", "Ansel", "Tobin"]


@dataclass
class StoryParams:
    setting: str
    task: str
    memory: str
    aid: str
    name: str
    gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for tid, task in TASKS.items():
            for mid, memory in MEMORIES.items():
                for aid_id, aid in AIDS.items():
                    if task.requires in aid.tags and task.requires in memory.tags:
                        combos.append((sid, tid, mid, aid_id))
    return combos


ASP_RULES = r"""
valid(S,T,M,A) :- setting(S), task(T), memory(M), aid(A),
                  task_requires(T,R), memory_touches(M,R), aid_handles(A,R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("task_requires", tid, t.requires))
    for mid, m in MEMORIES.items():
        lines.append(asp.fact("memory", mid))
        for tag in m.tags:
            lines.append(asp.fact("memory_touches", mid, tag))
    for aid_id, a in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        for tag in a.tags:
            lines.append(asp.fact("aid_handles", aid_id, tag))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if cl - py:
        print(" only in ASP:", sorted(cl - py))
    if py - cl:
        print(" only in Python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale day with a flashback and a practical ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--memory", choices=MEMORIES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
              and (args.task is None or c[1] == args.task)
              and (args.memory is None or c[2] == args.memory)
              and (args.aid is None or c[3] == args.aid)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, task, memory, aid = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_gender = args.helper_gender or ("boy" if gender == "girl" else "girl")
    helper = args.helper or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    return StoryParams(setting=setting, task=task, memory=memory, aid=aid, name=name, gender=gender, helper=helper, helper_gender=helper_gender)


def _note(world: World, p: str) -> None:
    world.say(p)


def tell(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, role="hero"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    setting = SETTINGS[params.setting]
    task = TASKS[params.task]
    memory = MEMORIES[params.memory]
    aid = AIDS[params.aid]
    world.facts.update(hero=hero, helper=helper, setting=setting, task=task, memory=memory, aid=aid)

    world.say(f"One {setting.weather} day, {hero.id} walked along {setting.place}.")
    world.say(f"{hero.id} had a simple wish: to {task.verb} before the day went dark.")
    world.say(f"{helper.id} came too, for no folk tale is wise when told alone.")
    world.para()
    world.say(f"But as the sun tilted low, the task grew tricky. {task.risk.capitalize()}.")
    world.say(f"{hero.id} paused, and {hero.pronoun('possessive')} eyes went far away.")
    world.say(
        f"There flashed a flashback -- {memory.ago}, when {memory.title.replace('flashback', '').strip()} taught {hero.id} that {memory.lesson}."
    )
    world.say(
        f"Because of that remembered day, {hero.id} did not hurry blindly. "
        f"Instead, {hero.id} chose {aid.label}, which {aid.use}."
    )
    world.para()
    world.say(
        f"Together, {hero.id} and {helper.id} worked until the task was done."
    )
    if params.task == "fetch_water":
        world.say(f"The pail reached home without spilling, and the doorstep stayed dry.")
    elif params.task == "mend_rope":
        world.say(f"The fence stood straight again, tied tight for the animals.")
    else:
        world.say(f"The bell rang at last, bright and clear, as if it had been waiting for them.")
    world.say(
        f"When night came, {setting.dusk_image}. {hero.id} smiled at the little change {hero.pronoun('subject')} had made."
    )
    world.facts["outcome"] = "done"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale story for a child that includes the word "day" and a flashback, with {f["hero"].id} finishing a small task before night.',
        f"Tell a warm village tale where {f['hero'].id} remembers an earlier lesson and uses {f['aid'].label} to solve a problem on the day.",
        f"Write a simple story in folk-tale style about a day, a flashback, and a helper who helps {f['hero'].id} make a practical choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    task = f["task"]
    aid = f["aid"]
    mem = f["memory"]
    setting = f["setting"]
    return [
        QAItem(
            question="What was the story about?",
            answer=f"It was about {hero.id} trying to {task.verb} on a single day. The tale also remembered an earlier day, and that memory helped guide the ending."
        ),
        QAItem(
            question=f"Why did {hero.id} stop and think before acting?",
            answer=f"{hero.id} remembered {mem.ago} and the lesson that {mem.lesson}. That flashback changed what {hero.pronoun('subject')} chose to do next."
        ),
        QAItem(
            question=f"How did {hero.id} finish the task?",
            answer=f"{hero.id} used {aid.label}, and {aid.use}. With {helper.id} beside {hero.pronoun('object')}, the work was finished before nightfall."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    setting = f["setting"]
    aid = f["aid"]
    mem = f["memory"]
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of the story that remembers an earlier time. It helps the reader understand why something in the present matters."
        ),
        QAItem(
            question=f"What does {aid.label} do in this tale?",
            answer=f"It helps the children solve the problem in a practical way. In this story, it is the tool that makes the work possible."
        ),
        QAItem(
            question=f"What kind of place is {setting.place}?",
            answer="It is a small, homely place where a simple task can feel important. That makes it a good place for a folk tale."
        ),
        QAItem(
            question="Why do folk tales often include a remembered lesson?",
            answer="Folk tales often use a remembered lesson to show how wisdom grows over time. A child learns from the past and makes a better choice now."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="village", task="fetch_water", memory="storm", aid="lantern", name="Mara", gender="girl", helper="Pip", helper_gender="boy"),
    StoryParams(setting="field", task="mend_rope", memory="promise", aid="needle", name="Tobin", gender="boy", helper="Nell", helper_gender="girl"),
    StoryParams(setting="wood", task="find_bell", memory="grandmother", aid="string", name="Elsa", gender="girl", helper="Bram", helper_gender="boy"),
]


def generate(params: StoryParams) -> StorySample:
    for field_name, table in [("setting", SETTINGS), ("task", TASKS), ("memory", MEMORIES), ("aid", AIDS)]:
        if getattr(params, field_name) not in table:
            raise StoryError(f"invalid {field_name}: {getattr(params, field_name)!r}")
    world = tell(params)
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


def asp_verify_smoke() -> int:
    rc = asp_verify()
    try:
        sample = generate(CURATED[0])
        assert sample.story
    except Exception as e:
        print(f"SMOKE FAIL: {e}")
        return 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify_smoke())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/4."))
        vals = sorted(set(asp.atoms(model, "valid")))
        for v in vals:
            print(v)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                i += 1
                continue
            seen.add(s.story)
            samples.append(s)
            i += 1
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
