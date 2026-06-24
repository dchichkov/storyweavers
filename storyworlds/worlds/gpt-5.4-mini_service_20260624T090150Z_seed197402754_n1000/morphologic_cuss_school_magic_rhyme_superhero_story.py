#!/usr/bin/env python3
"""
Standalone storyworld: Morphologic Cuss School Magic Rhyme Superhero Story.

A small school-set superhero tale world in which a young hero notices a hurtful
cuss word, uses a little magic and a rhyme to change the mood, and helps class
end in a calmer, kinder way.

The domain is intentionally tiny and state-driven:
- physical meters track loudness, mess, sparkle, and calm
- emotional memes track worry, courage, anger, relief, and pride
- the story is generated from a simulated school scene, not from a frozen prompt

This file follows the Storyweavers world contract:
- self-contained stdlib script
- eager results import
- lazy asp import inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    wearing: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher"}
        male = {"boy", "father", "man", "teacher"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def obj(self) -> str:
        return "them" if self.plural else "it"

    @property
    def short(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str = "the school"
    affordances: set[str] = field(default_factory=set)


@dataclass
class Power:
    id: str
    title: str
    action: str
    effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Trouble:
    id: str
    label: str
    phrase: str
    noise: str
    problem: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    covers: set[str]
    prep: str
    end: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    lines: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.lines = [[]]
        w.facts = dict(self.facts)
        return w


def _m(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def _e(entity: Entity, key: str) -> float:
    return entity.memes.get(key, 0.0)


def _add_m(entity: Entity, key: str, val: float) -> None:
    entity.meters[key] = _m(entity, key) + val


def _add_e(entity: Entity, key: str, val: float) -> None:
    entity.memes[key] = _e(entity, key) + val


def _set_e(entity: Entity, key: str, val: float) -> None:
    entity.memes[key] = val


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for ent in list(world.entities.values()):
            if _m(ent, "loud") >= THRESHOLD and _e(ent, "worry") >= THRESHOLD:
                sig = ("shake", ent.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    _add_e(ent, "fear", 1)
                    out.append(f"{ent.short} flinched at the noisy words.")
                    changed = True
            if _m(ent, "sparkle") >= THRESHOLD and _e(ent, "anger") >= THRESHOLD:
                sig = ("magic_calms", ent.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    _add_e(ent, "calm", 1)
                    _set_e(ent, "anger", max(0.0, _e(ent, "anger") - 1))
                    out.append(f"The little magic made the anger shrink.")
                    changed = True
            if _m(ent, "rhyme") >= THRESHOLD and _e(ent, "fear") >= THRESHOLD:
                sig = ("rhyme_courage", ent.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    _add_e(ent, "courage", 1)
                    _set_e(ent, "fear", max(0.0, _e(ent, "fear") - 1))
                    out.append(f"The rhyme gave {ent.short} a brave heart.")
                    changed = True
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict(world: World, hero: Entity, trouble: Trouble) -> bool:
    sim = world.copy()
    _stumble(sim, sim.get(hero.id), trouble, narrate=False)
    return _m(sim.get("classroom"), "calm") < THRESHOLD


def _stumble(world: World, hero: Entity, trouble: Trouble, narrate: bool = True) -> None:
    _add_m(world.get("hall"), "loud", 1)
    _add_e(hero, "worry", 1)
    if trouble.problem == "hurt":
        _add_e(world.get("classroom"), "anger", 1)
    propagate(world, narrate=narrate)


def enter_school(world: World, hero: Entity, teacher: Entity, trouble: Trouble) -> None:
    world.say(f"{hero.short} arrived at the school with a backpack full of notebooks and hope.")
    world.say(f"{hero.pronoun().capitalize()} liked the bright halls, the bell, and the neat rows of desks.")
    world.say(f"Then a sharp cuss word bounced down the hall and made the room feel smaller.")


def notice_trouble(world: World, hero: Entity, trouble: Trouble) -> None:
    _add_e(hero, "worry", 1)
    _add_m(world.get("hall"), "loud", 1)
    world.say(f"{hero.short} heard the word {trouble.label} and knew it could sting like a shove.")


def act_magic(world: World, hero: Entity, trouble: Trouble, power: Power) -> None:
    _add_m(hero, "sparkle", 1)
    _add_e(hero, "courage", 1)
    world.say(
        f"{hero.short} lifted {hero.pronoun('possessive')} hands and used {power.title}, "
        f"the special school magic that could soften a bad moment."
    )
    world.say(f"{hero.pronoun().capitalize()} whispered, \"{power.action}, {power.effect}!\"")
    _add_m(world.get("hall"), "sparkle", 1)
    propagate(world)


def act_rhyme(world: World, hero: Entity, trouble: Trouble, power: Power) -> None:
    _add_m(hero, "rhyme", 1)
    _add_e(hero, "pride", 1)
    world.say(
        f"Then {hero.short} added a tiny rhyme, because rhyme could turn a hurtful sound into a silly sound."
    )
    world.say(
        f"\"No more {trouble.label} in the air, let words be kind and words be fair,\" "
        f"{hero.pronoun()} sang."
    )
    _add_m(world.get("classroom"), "rhyme", 1)
    _set_e(world.get("classroom"), "anger", max(0.0, _e(world.get("classroom"), "anger") - 1))
    _add_e(world.get("classroom"), "calm", 1)
    propagate(world)


def resolve(world: World, hero: Entity, teacher: Entity, trouble: Trouble, tool: Tool) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    _set_e(world.get("classroom"), "fear", max(0.0, _e(world.get("classroom"), "fear") - 1))
    _add_e(world.get("classroom"), "calm", 1)
    world.say(
        f"At last, the school felt safe again. The mean word lost its sharp edge, and the room grew gentle."
    )
    world.say(
        f"{teacher.short} smiled at {hero.short} and thanked {hero.pronoun('object')} for helping with a brave, kind fix."
    )
    world.say(
        f"{hero.short} stood tall, and the old cuss word was only a silly sound now; "
        f"the hallway ended in quiet steps, tidy desks, and a calm bell."
    )


def tell(world: World, hero: Entity, teacher: Entity, trouble: Trouble, power: Power, tool: Tool) -> World:
    enter_school(world, hero, teacher, trouble)
    world.para()
    notice_trouble(world, hero, trouble)
    world.say(f"{hero.short} did not want the hall to stay mean and noisy.")
    world.para()
    act_magic(world, hero, trouble, power)
    act_rhyme(world, hero, trouble, power)
    world.para()
    resolve(world, hero, teacher, trouble, tool)
    world.facts.update(hero=hero, teacher=teacher, trouble=trouble, power=power, tool=tool)
    return world


SETTINGS = {
    "school": Setting(place="the school", affordances={"hallway", "classroom", "lunchroom"}),
}

POWERS = {
    "magic": Power(
        id="magic",
        title="Magic",
        action="sparkle",
        effect="mend the mood",
        tags={"magic", "school"},
    ),
    "rhyme": Power(
        id="rhyme",
        title="Rhyme",
        action="hum",
        effect="make the words kind",
        tags={"rhyme", "school"},
    ),
}

TROUBLES = {
    "cuss": Trouble(
        id="cuss",
        label="cuss",
        phrase="a cuss word",
        noise="sharp",
        problem="hurt",
        tags={"cuss", "school"},
    ),
    "morphologic": Trouble(
        id="morphologic",
        label="morphologic",
        phrase="a morphologic mix-up",
        noise="twisty",
        problem="confuse",
        tags={"morphologic", "school"},
    ),
}

TOOLS = {
    "badge": Tool(
        id="badge",
        label="superhero badge",
        phrase="a shiny superhero badge",
        helps={"magic"},
        covers={"chest"},
        prep="pin on the badge",
        end="pinned the badge back on",
    ),
    "book": Tool(
        id="book",
        label="rhyming book",
        phrase="a small rhyming book",
        helps={"rhyme"},
        covers={"hands"},
        prep="open the rhyming book",
        end="closed the rhyming book with care",
    ),
}

HERO_NAMES = ["Maya", "Noah", "Ivy", "Leo", "Ava", "Finn", "Zoe", "Eli"]
TEACHER_NAMES = ["Ms. Lane", "Mr. Reed", "Ms. Park", "Mr. Cole"]


@dataclass
class StoryParams:
    setting: str
    trouble: str
    power: str
    tool: str
    name: str
    teacher: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="School superhero storyworld with magic and rhyme.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--power", choices=POWERS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--teacher", choices=TEACHER_NAMES)
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
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TROUBLES:
        lines.append(asp.fact("trouble", tid))
    for pid, p in POWERS.items():
        lines.append(asp.fact("power", pid))
        for t in sorted(p.tags):
            lines.append(asp.fact("tags_power", pid, t))
    for uid, u in TOOLS.items():
        lines.append(asp.fact("tool", uid))
        for h in sorted(u.helps):
            lines.append(asp.fact("helps", uid, h))
        for c in sorted(u.covers):
            lines.append(asp.fact("covers", uid, c))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S, T, P, U) :- setting(S), trouble(T), power(P), tool(U),
                           tags_power(P, school), helps(U, P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    py_set = set((s, t, p, u) for s in SETTINGS for t in TROUBLES for p in POWERS for u in TOOLS if p == "magic" or p == "rhyme")
    if clingo_set == py_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("only in clingo:", sorted(clingo_set - py_set))
    print("only in python:", sorted(py_set - clingo_set))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or "school"
    trouble = args.trouble or rng.choice(list(TROUBLES))
    power = args.power or rng.choice(list(POWERS))
    tool = args.tool or ("badge" if power == "magic" else "book")
    if power == "magic" and tool != "badge":
        raise StoryError("Magic needs the superhero badge in this tiny world.")
    if power == "rhyme" and tool != "book":
        raise StoryError("Rhyme needs the rhyming book in this tiny world.")
    name = args.name or rng.choice(HERO_NAMES)
    teacher = args.teacher or rng.choice(TEACHER_NAMES)
    return StoryParams(setting=setting, trouble=trouble, power=power, tool=tool, name=name, teacher=teacher)


def reasonableness_gate(params: StoryParams) -> None:
    if params.setting != "school":
        raise StoryError("This world is only set at school.")
    if params.trouble not in TROUBLES:
        raise StoryError("Unknown trouble.")
    if params.power not in POWERS:
        raise StoryError("Unknown power.")
    if params.tool not in TOOLS:
        raise StoryError("Unknown tool.")
    if params.power not in TOOLS[params.tool].helps:
        raise StoryError("That tool does not fit that power in this story world.")


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    setting = SETTINGS[params.setting]
    trouble = TROUBLES[params.trouble]
    power = POWERS[params.power]
    tool = TOOLS[params.tool]

    world = World(setting)
    world.add(Entity(id="hall", kind="place", type="place", label="hallway", meters={"loud": 0}, memes={"calm": 0}))
    world.add(Entity(id="classroom", kind="place", type="place", label="classroom", meters={"sparkle": 0, "rhyme": 0}, memes={"calm": 0, "anger": 0, "fear": 0}))
    hero = world.add(Entity(id=params.name, kind="character", type="girl" if params.name in {"Maya", "Ivy", "Ava", "Zoe"} else "boy", label=params.name, memes={"worry": 0, "courage": 0, "pride": 0, "relief": 0}))
    teacher = world.add(Entity(id="teacher", kind="character", type="teacher", label=params.teacher, memes={"calm": 0}))

    tell(world, hero, teacher, trouble, power, tool)

    prompts = [
        f'Write a short superhero story set at school that includes "{trouble.label}" and ends with kindness.',
        f"Tell a gentle story where {hero.short} uses {power.title} and a rhyme to help when a cuss word causes trouble.",
        f'Write a child-friendly school story with a magic hero, a rhyme, and the word "{trouble.label}".',
    ]

    story_qa = [
        QAItem(
            question=f"Where did {hero.short} help when the trouble started?",
            answer=f"{hero.short} helped at the school, in the hallway and classroom, where the cuss word made everyone uneasy.",
        ),
        QAItem(
            question=f"What did {hero.short} use to help with the bad word?",
            answer=f"{hero.short} used {power.title} and then a rhyme, which made the moment calmer and kinder.",
        ),
        QAItem(
            question=f"How did the school feel at the end?",
            answer="It felt calm again. The mean sound lost its sharp edge, and the class could breathe easy.",
        ),
    ]

    if trouble.id == "cuss":
        story_qa.append(QAItem(
            question=f"Why was the cuss word a problem?",
            answer="It was a problem because it sounded sharp and could hurt feelings, so the hero tried to change the moment.",
        ))
    if power.id == "magic":
        story_qa.append(QAItem(
            question=f"What did the magic do in the story?",
            answer="The magic made the mood sparkle and helped the anger get smaller.",
        ))
    if power.id == "rhyme":
        story_qa.append(QAItem(
            question=f"Why did the rhyme matter?",
            answer="The rhyme turned the sound silly and helped courage replace fear.",
        ))

    world_qa = [
        QAItem(
            question="What is a school?",
            answer="A school is a place where children go to learn, read, count, and practice being together kindly.",
        ),
        QAItem(
            question="What does a superhero badge suggest?",
            answer="A superhero badge can suggest bravery, helping, and a promise to do the right thing.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like cat and hat, which can make speech fun to say.",
        ),
    ]

    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World questions ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


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
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible story combos:\n")
        for s, t, p, u in stories:
            print(f"  {s:8} {t:10} {p:8} {u:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for trouble in TROUBLES:
            power = "magic" if trouble == "cuss" else "rhyme"
            tool = "badge" if power == "magic" else "book"
            params = StoryParams(setting="school", trouble=trouble, power=power, tool=tool, name="Maya", teacher="Ms. Lane")
            params.seed = base_seed
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.name}: {p.trouble} with {p.power} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
