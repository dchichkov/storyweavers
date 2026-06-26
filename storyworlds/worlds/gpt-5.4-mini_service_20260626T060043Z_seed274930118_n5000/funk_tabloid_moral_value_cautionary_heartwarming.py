#!/usr/bin/env python3
"""
storyworlds/worlds/funk_tabloid_moral_value_cautionary_heartwarming.py
=======================================================================

A small heartwarming storyworld about a child, a bit of funk music, and a
tabloid rumor that causes a gentle cautionary problem before a truthful,
moral-value resolution.

Premise:
- A child loves playing funk music in a small community space.
- A tabloid page and its shiny headline can make a harmless moment look mean.
- A caring adult worries about honesty, kindness, and the risk of public shame.

Turn:
- The child sees how a careless tabloid story can hurt someone by spreading a
  wrong idea faster than the truth.
- The adult and child decide not to fight with louder gossip, but to answer
  with a kind, honest performance and a clear apology.

Resolution:
- The child plays a warm little funk tune that helps the upset person smile.
- The final image proves the change: the tabloid is set aside, the truth is
  shared, and the room feels brighter than before.

This script follows the Storyweavers contract:
- typed entities with meters and memes
- live world model drives prose
- inline ASP twin plus Python reasonableness gate
- standalone stdlib script with QA and trace output
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

# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------

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
    worn_by: Optional[str] = None
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mess": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "hurt": 0.0, "truth": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

@dataclass
class Setting:
    place: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    caution: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class Tool:
    id: str
    label: str
    prep: str
    tags: set[str] = field(default_factory=set)
    protective: bool = False
    plural: bool = False


SETTINGS = {
    "community_center": Setting(place="the community center", indoors=True, affords={"funk_rehearsal", "poster_making"}),
    "hall": Setting(place="the town hall", indoors=True, affords={"funk_rehearsal", "poster_making"}),
    "kitchen": Setting(place="the kitchen", indoors=True, affords={"poster_making"}),
}

ACTIVITIES = {
    "funk_rehearsal": Activity(
        id="funk_rehearsal",
        verb="play funk music",
        gerund="playing funk music",
        rush="start the band too loudly",
        mess="noise",
        caution="loud rumors can carry farther than the truth",
        tags={"funk", "music", "truth"},
    ),
    "poster_making": Activity(
        id="poster_making",
        verb="make a poster",
        gerund="making a poster",
        rush="scribble before checking the facts",
        mess="ink",
        caution="fast headlines can be unfair",
        tags={"tabloid", "paper", "truth"},
    ),
}

PRIZES = {
    "flyer": Prize(id="flyer", label="flyer", phrase="a bright community flyer", type="flyer", region="hands"),
    "crown": Prize(id="crown", label="paper crown", phrase="a glittery paper crown", type="crown", region="head"),
    "shirt": Prize(id="shirt", label="shirt", phrase="a clean white shirt", type="shirt", region="torso"),
}

TOOLS = [
    Tool(id="truth_note", label="a truth note", prep="write a careful note with the real details", tags={"truth"}),
    Tool(id="guitar_case", label="the guitar case", prep="put the guitar case beside the stage", tags={"funk", "music"}),
    Tool(id="editor_pen", label="an editor's pen", prep="cross out the unfair line and write the facts", tags={"tabloid", "truth"}),
]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    if activity.id == "funk_rehearsal":
        return prize.region in {"hands", "torso"}
    if activity.id == "poster_making":
        return prize.region in {"hands", "torso"}
    return False


def select_tool(activity: Activity, prize: Prize) -> Optional[Tool]:
    needed = "truth" if activity.id == "poster_making" else "funk"
    for tool in TOOLS:
        if needed in tool.tags:
            return tool
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_tool(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
prize_at_risk(A,P) :- activity(A), prize(P), affects(A,R), worn_on(P,R).
has_tool(A,P) :- prize_at_risk(A,P), tool(T), fits(T,A).
valid(Place,A,P) :- setting(Place), affords(Place,A), prize_at_risk(A,P), has_tool(A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in sorted({"hands", "torso"} if aid in {"funk_rehearsal", "poster_making"} else set()):
            lines.append(asp.fact("affects", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for tag in sorted(t.tags):
            lines.append(asp.fact("fits", t.id, "funk_rehearsal" if tag == "funk" else "poster_making"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and python gate:")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def warn_about_tabloid(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["worry"] += 1
    world.say(
        f'"Be careful," {parent.pronoun("possessive")} {parent.label_word} said. '
        f'"A tabloid headline can make a small mistake look huge, and that is not kind."'
    )
    world.say(
        f"{hero.pronoun().capitalize()} looked at the {prize.label} and nodded, because {activity.caution}."
    )


def expose_rumor(world: World, hero: Entity, rival: Entity, activity: Activity) -> None:
    hero.memes["hurt"] += 1
    rival.memes["hurt"] += 1
    world.say(
        f"Then a tabloid page fluttered open with a loud headline, and it made {rival.id} look silly."
    )
    world.say(
        f"{hero.id} frowned. {hero.pronoun().capitalize()} knew that a funny story was not the same as the truth."
    )


def choose_truthful_fix(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Tool:
    tool = select_tool(activity, prize)
    if tool is None:
        raise StoryError("No honest fix fits this story shape.")
    world.say(
        f"{parent.pronoun('possessive').capitalize()} {parent.label_word} pointed to {tool.label} and said, "
        f'"Let us fix this with the real facts."'
    )
    return tool


def kind_turn(world: World, hero: Entity, rival: Entity, tool: Tool) -> None:
    hero.memes["truth"] += 1
    hero.memes["joy"] += 1
    rival.memes["hurt"] = max(0.0, rival.memes["hurt"] - 1)
    world.say(
        f"{hero.id} used {tool.label} and {tool.prep}, then walked over to {rival.id} and told the whole truth."
    )
    world.say(
        f"{rival.id}'s face softened. The room felt warm again, because the apology was real."
    )


def ending_image(world: World, hero: Entity, rival: Entity) -> None:
    world.say(
        f"By the end, the tabloid page was folded away, {hero.id} was smiling beside {rival.id}, "
        f"and the little funk rhythm sounded cheerful instead of sharp."
    )


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------

def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Mina", hero_type: str = "girl",
         parent_type: str = "mother", rival_name: str = "Nico") -> World:
    world = World(setting.place)

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    rival = world.add(Entity(id=rival_name, kind="character", type="boy", label=rival_name))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase))
    tool = None

    world.say(
        f"{hero.id} loved the warm bounce of funk music and the way a room could smile after a good beat."
    )
    world.say(
        f"At {setting.place}, {hero.id} was helping with {activity.gerund}, and {prize.phrase} sat nearby."
    )

    world.para()
    warn_about_tabloid(world, parent, hero, activity, prize)
    expose_rumor(world, hero, rival, activity)

    world.para()
    tool = choose_truthful_fix(world, parent, hero, activity, prize)
    kind_turn(world, hero, rival, tool)
    ending_image(world, hero, rival)

    world.facts.update(
        hero=hero,
        parent=parent,
        rival=rival,
        prize=prize,
        activity=activity,
        setting=setting,
        tool=tool,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Story params and QA
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    rival: str
    seed: Optional[int] = None


NAMES = ["Mina", "Luca", "Tess", "Owen", "Ari", "Nia"]
RIVAL_NAMES = ["Nico", "Ivy", "Jules", "Rae", "Pip", "Milo"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a heartwarming cautionary story about funk music, a tabloid rumor, and telling the truth.',
        f"Tell a gentle story where {f['hero'].id} at {f['setting'].place} learns that a tabloid headline can be unfair.",
        f'Write a child-friendly story that includes the words "funk" and "tabloid" and ends with a kind apology.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    rival = f["rival"]
    activity = f["activity"]
    prize = f["prize"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"Who learned that the tabloid headline was unfair?",
            answer=f"{hero.id} learned that the tabloid headline was unfair and that the truth mattered more than gossip.",
        ),
        QAItem(
            question=f"What did {hero.id} love doing in the story?",
            answer=f"{hero.id} loved {activity.gerund}, especially because funk music made the room feel happy.",
        ),
        QAItem(
            question=f"Why did the parent worry about the tabloid page?",
            answer=f"{parent.id} worried because a tabloid can spread a wrong idea quickly, and that can hurt someone's feelings.",
        ),
        QAItem(
            question=f"How did the child fix the problem?",
            answer=f"{hero.id} used {tool.label} and told the real story kindly, which helped {rival.id} feel better.",
        ),
        QAItem(
            question=f"What was true at the end?",
            answer=f"At the end, the tabloid page was put away, the apology was honest, and the funk rhythm felt warm again.",
        ),
    ]


KNOWLEDGE = {
    "funk": [
        QAItem(
            question="What is funk music?",
            answer="Funk is a style of music with a strong beat that can make people want to tap their feet and dance.",
        )
    ],
    "tabloid": [
        QAItem(
            question="What is a tabloid?",
            answer="A tabloid is a newspaper or page that often uses big, attention-grabbing headlines.",
        )
    ],
    "truth": [
        QAItem(
            question="Why is it important to tell the truth?",
            answer="Telling the truth helps people trust each other and keeps rumors from hurting someone's feelings.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    for tag in ["funk", "tabloid", "truth"]:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="community_center", activity="funk_rehearsal", prize="shirt", name="Mina", gender="girl", parent="mother", rival="Nico"),
    StoryParams(place="hall", activity="poster_making", prize="flyer", name="Luca", gender="boy", parent="father", rival="Ivy"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} does not reasonably put {prize.label} at risk in this world.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming cautionary storyworld about funk, tabloid rumors, and truth.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--rival")
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
    if args.activity and args.prize:
        act, prize = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, prize) and select_tool(act, prize)):
            raise StoryError(explain_rejection(act, prize))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    rival = args.rival or rng.choice(RIVAL_NAMES)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, rival=rival)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent, params.rival)
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


def asp_facts() -> str:
    return asp_facts.__wrapped__()  # type: ignore[attr-defined]


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible (place, activity, prize) combos:\n")
        for place, activity, prize in combos:
            print(f"  {place:16} {activity:16} {prize}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
