#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/display_lore_lesson_learned_flashback_fable.py
==============================================================================

A standalone tiny storyworld for a fable-like tale about a child, a display of
old family lore, a tempting shortcut, a flashback, and a lesson learned.

Core premise:
- A child wants to improve a village display about an old animal tale.
- They are tempted to invent a shiny detail that is not true.
- A flashback reminds them of an earlier mistake.
- A wiser helper warns them.
- They fix the display by telling the lore plainly.
- The ending proves the lesson learned: truth makes the display stronger.

This script follows the Storyweavers contract:
- typed entities with meters and memes
- state-driven prose
- grounded QA
- Python reasonableness gate plus inline ASP twin
- standalone stdlib script with the shared result containers
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
TRUTH_MIN = 2
FLASHBACK_MIN = 1
LESSON_MIN = 1


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
    mood: str
    display_name: str
    allow_flashback: bool = True


@dataclass
class LoreItem:
    id: str
    subject: str
    truth: str
    embellishment: str
    display_piece: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Temptation:
    id: str
    idea: str
    lie: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Guide:
    id: str
    label: str
    advice: str
    flashback_trigger: str
    repair: str
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_flashback(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.meters["tempted"] >= THRESHOLD and child.memes["remember"] >= FLASHBACK_MIN:
        sig = ("flashback",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["shame"] += 1
            out.append("__flashback__")
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    guide = world.entities.get("guide")
    if not child or not guide:
        return out
    if child.memes["truth"] >= TRUTH_MIN and child.memes["lesson"] >= LESSON_MIN:
        sig = ("lesson",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["pride"] += 1
            out.append("__lesson__")
    return out


CAUSAL_RULES = [
    Rule("flashback", "memory", _r_flashback),
    Rule("lesson", "social", _r_lesson),
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


def reasonableness_ok(setting: Setting, lore: LoreItem, temptation: Temptation, guide: Guide) -> bool:
    return (
        setting.allow_flashback
        and lore.truth
        and temptation.lie
        and guide.repair
        and len(lore.display_piece) > 0
    )


def build_flashback(world: World, child: Entity, guide: Entity, setting: Setting, lore: LoreItem) -> None:
    child.memes["remember"] += 1
    child.memes["worry"] += 1
    world.say(
        f"As {child.id} polished the {setting.display_name}, a flashback tugged at {child.pronoun('possessive')} mind. "
        f"Once before, {child.id} had made a story sound grander than it was, and the crowd had gone quiet."
    )
    world.say(
        f"{guide.label_word.capitalize()} noticed the pause. \"Remember the old lore,\" {guide.pronoun()} said softly. "
        f"\"A story can be small and still be strong when it is true.\""
    )
    child.memes["truth"] += 1
    child.memes["lesson"] += 1


def tell_setup(world: World, child: Entity, guide: Entity, setting: Setting, lore: LoreItem) -> None:
    child.memes["curious"] += 1
    child.memes["joy"] += 1
    world.say(
        f"On market day, {child.id} helped arrange {setting.mood} by the village lane. "
        f"The {setting.display_name} was meant to teach the children the old lore of {lore.subject}."
    )
    world.say(
        f"{guide.label_word.capitalize()} had laid out {lore.display_piece}, and {child.id} liked how the little display caught the light."
    )


def tempt(world: World, child: Entity, temptation: Temptation, lore: LoreItem) -> None:
    child.meters["tempted"] += 1
    child.memes["vanity"] += 1
    world.say(
        f"Then {child.id} had a shiny idea: {temptation.idea}. It sounded clever, but it would have bent the lore into a lie."
    )
    world.say(
        f"{child.id} imagined the crowd clapping louder if the display said {temptation.lie}, even though that was not how it had happened."
    )


def warn(world: World, guide: Entity, child: Entity, temptation: Temptation, lore: LoreItem) -> None:
    world.say(
        f"{guide.label_word.capitalize()} shook {guide.pronoun('possessive')} head. \"That would twist the {lore.subject} tale,\" {guide.pronoun()} said. "
        f"\"A display should honor the truth, not dress it up.\""
    )
    world.facts["warning"] = temptation.risk


def fix_display(world: World, child: Entity, guide: Entity, setting: Setting, lore: LoreItem, temptation: Temptation) -> None:
    child.memes["truth"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"That warning woke an old memory in {child.id}. In a flashback, {child.id} remembered how the proud little lie had turned sour before."
    )
    world.say(
        f"So {child.id} took a breath, erased the false sparkle, and wrote the lore plainly: {lore.truth}."
    )
    world.say(
        f"{guide.label_word.capitalize()} smiled. The display stood steady at the {setting.display_name}, simple and bright, and everyone understood it better."
    )


def ending(world: World, child: Entity, guide: Entity, lore: LoreItem) -> None:
    world.say(
        f"By sunset, {child.id} was not chasing applause anymore. {child.id} was guarding the old story, and that made {child.id} feel tall."
    )
    world.say(
        f"The lesson learned was simple: when a tale is true, it does not need glitter to shine. Even the old lore could glow in a humble display."
    )


def tell(setting: Setting, lore: LoreItem, temptation: Temptation, guide_cfg: Guide,
         child_name: str = "Mina", child_gender: str = "girl", parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    guide = world.add(Entity(id="Guide", kind="character", type=parent_type, role="guide", label=guide_cfg.label))

    tell_setup(world, child, guide, setting, lore)
    world.para()
    tempt(world, child, temptation, lore)
    warn(world, guide, child, temptation, lore)
    build_flashback(world, child, guide, setting, lore)
    world.para()
    fix_display(world, child, guide, setting, lore, temptation)
    ending(world, child, guide, lore)

    world.facts.update(
        child=child,
        guide=guide,
        setting=setting,
        lore=lore,
        temptation=temptation,
        guide_cfg=guide_cfg,
        resolved=True,
        flashback=child.memes["remember"] >= FLASHBACK_MIN,
        lesson=child.memes["lesson"] >= LESSON_MIN,
    )
    return world


SETTINGS = {
    "lantern_hall": Setting("lantern_hall", "lantern hall", "a quiet hall", "display board"),
    "village_square": Setting("village_square", "village square", "the square on festival morning", "display stand"),
    "school_corner": Setting("school_corner", "school corner", "the small reading nook", "display shelf"),
}

LORE = {
    "owl": LoreItem(
        "owl",
        "an old owl",
        "The old owl once watched over the orchard through the night.",
        "The old owl was the tallest and brightest guardian in the whole forest.",
        "a painted owl plaque and a nest of straw",
        "Old stories should be told true, because truth keeps them strong.",
        tags={"lore", "display", "owl"},
    ),
    "oak": LoreItem(
        "oak",
        "an ancient oak",
        "The ancient oak sheltered travelers during the storm.",
        "The ancient oak never lost a leaf, even in the hardest storm.",
        "a carved oak board and a ring of leaves",
        "True tales make wise roots for young hearts.",
        tags={"lore", "display", "tree"},
    ),
    "fox": LoreItem(
        "fox",
        "a clever fox",
        "The clever fox shared berries only after the smaller animals had eaten.",
        "The clever fox fed every animal in the forest by itself.",
        "a fox picture and a little bowl of berries",
        "A story can be gentle without being made up.",
        tags={"lore", "display", "fox"},
    ),
}

TEMPTATIONS = {
    "glitter": Temptation(
        "glitter",
        "add glitter and a gold ribbon to make the display look grand",
        "the tallest and brightest guardian",
        "It would make the old tale sound bigger than it was",
        tags={"display", "lie"},
    ),
    "thunder": Temptation(
        "thunder",
        "draw lightning around the picture so everyone stares at it",
        "the fox chased the storm by itself",
        "It would turn the small true story into a loud pretend one",
        tags={"display", "lie"},
    ),
    "crown": Temptation(
        "crown",
        "put a paper crown on the animal to make it seem royal",
        "the oak bowed to every traveler",
        "It would dress the lore in a costume that did not belong",
        tags={"display", "lie"},
    ),
}

GUIDES = {
    "mother": Guide("mother", "mom", "keep it true", "old mistake", "write it plainly", tags={"lesson", "flashback"}),
    "father": Guide("father", "dad", "tell it straight", "proud mistake", "set it right", tags={"lesson", "flashback"}),
}

NAMES = ["Mina", "Tessa", "Nora", "Pip", "Lina", "Rory", "Jules", "Sage"]
GENDERS = ["girl", "boy"]


@dataclass
class StoryParams:
    setting: str
    lore: str
    temptation: str
    guide: str
    child_name: str
    child_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for l in LORE:
            for t in TEMPTATIONS:
                for g in GUIDES:
                    if reasonableness_ok(SETTINGS[s], LORE[l], TEMPTATIONS[t], GUIDES[g]):
                        combos.append((s, l, t))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    lore = f["lore"]
    return [
        f'Write a fable-like story that includes the words "display" and "lore".',
        f"Tell a short tale where {child.id} tends a village display about {lore.subject}, has a flashback, and learns an honest lesson.",
        f"Write a child-facing fable in which a tempting idea is rejected because an old lesson learned says the truth matters more than glitter.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    guide = f["guide"]
    lore = f["lore"]
    tempt = f["temptation"]
    setting = f["setting"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, who was helping with a village display and learning how to tell an old lore story honestly."),
        ("What did {0} want to do?".format(child.id),
         f"{child.id} wanted to make the display look grander by using {tempt.idea}, but that would have bent the truth."),
        ("What did the guide remind the child?",
         f"{guide.label_word.capitalize()} reminded {child.id} that a display should honor the truth and not dress up the lore with a lie."),
        ("What changed by the end?",
         f"{child.id} rewrote the display plainly, so the {setting.display_name} showed {lore.truth.lower()} instead of a made-up version. The lesson learned was that truth makes a story stronger."),
    ]
    if f.get("flashback"):
        qa.append((
            "Why was there a flashback?",
            f"The flashback happened because {child.id} remembered an earlier time when a proud little lie had gone wrong. That memory helped {child.id} choose the honest version this time."
        ))
    if f.get("lesson"):
        qa.append((
            "What lesson was learned?",
            f"The lesson learned was that old lore should be told plainly. A true display may be quieter, but it is kinder and stronger."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["lore"].tags) | set(f["temptation"].tags) | set(f["guide_cfg"].tags)
    out = []
    knowledge = {
        "display": [("What is a display?", "A display is something arranged so people can look at it and learn from it.")],
        "lore": [("What is lore?", "Lore is an old story or piece of shared wisdom that people pass down.")],
        "flashback": [("What is a flashback in a story?", "A flashback is a moment when a story briefly remembers something that happened earlier.")],
        "lesson": [("What does it mean to learn a lesson?", "It means someone understands a better way to act after seeing what went wrong or what helped.")],
    }
    for tag in ["display", "lore", "flashback", "lesson"]:
        if tag in tags:
            out.extend(knowledge[tag])
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("lantern_hall", "owl", "glitter", "mother", "Mina", "girl"),
    StoryParams("village_square", "oak", "thunder", "father", "Pip", "boy"),
    StoryParams("school_corner", "fox", "crown", "mother", "Nora", "girl"),
]


def explain_rejection() -> str:
    return "(No story: the requested pieces do not make a reasonable fable-like display-and-lore lesson.)"


def tell_from_params(params: StoryParams) -> World:
    return tell(
        SETTINGS[params.setting],
        LORE[params.lore],
        TEMPTATIONS[params.temptation],
        GUIDES[params.guide],
        params.child_name,
        params.child_gender,
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.lore is None or c[1] == args.lore)
              and (args.temptation is None or c[2] == args.temptation)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, lore, temptation = rng.choice(sorted(combos))
    guide = args.guide or rng.choice(sorted(GUIDES))
    child_gender = args.child_gender or rng.choice(GENDERS)
    child_name = args.child_name or rng.choice(NAMES)
    return StoryParams(setting, lore, temptation, guide, child_name, child_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell_from_params(params)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-like story world about display, lore, flashback, and lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--lore", choices=LORE)
    ap.add_argument("--temptation", choices=TEMPTATIONS)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=GENDERS)
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


ASP_RULES = r"""
valid(S,L,T) :- setting(S), lore(L), temptation(T), good_combo(S,L,T).
flashback :- tempted, remember, allow_flashback.
lesson :- truth, lesson_mark.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for lid in LORE:
        lines.append(asp.fact("lore", lid))
    for tid in TEMPTATIONS:
        lines.append(asp.fact("temptation", tid))
    for gid in GUIDES:
        lines.append(asp.fact("guide", gid))
    lines.append(asp.fact("allow_flashback", "yes"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid_combo gates differ.")
    sample = generate(CURATED[0])
    if not sample.story.strip():
        return 1
    print("OK: ASP gate matches Python gate and generate() produced a story.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
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
            header = f"### {p.child_name}: {p.lore} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
