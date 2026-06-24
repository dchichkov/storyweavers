#!/usr/bin/env python3
"""
A small comedy-flavored storyworld about a girl, a band, and a funny problem
that turns into a better performance.

Seed sketch:
---
A girl wants to play in a band. The band is getting ready for a small show, but
the girl keeps making everyone laugh at the wrong moment. The band starts to
fall apart because they cannot keep a straight face. Then the girl turns the
joke into part of the act, everyone relaxes, and the band finishes together.

World model idea:
---
- The girl has joy, nerves, and a sense of humor.
- The band has tempo, focus, and togetherness.
- A funny prop or joke can raise laughter too high and break the rhythm.
- A good joke, shared at the right time, helps the band recover and perform.
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
    kind: str = "thing"     # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister"}
        male = {"boy", "man", "father", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the school gym"
    affords: set[str] = field(default_factory=set)


@dataclass
class Act:
    id: str
    verb: str
    gerund: str
    mess: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gadget:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    prep: str = ""
    tail: str = ""


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraph_breaks: set[int] = set()
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        self.paragraph_breaks.add(len(self.lines))

    def render(self) -> str:
        out: list[str] = []
        for i, line in enumerate(self.lines):
            if i in self.paragraph_breaks and out:
                out.append("")
            out.append(line)
        return "\n".join(out)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "gym": Setting(place="the school gym", affords={"joke", "juggle"}),
    "stage": Setting(place="the little stage at the park", affords={"joke", "dance"}),
    "garage": Setting(place="the garage band room", affords={"joke", "drum"}),
}

ACTS = {
    "joke": Act(
        id="joke",
        verb="tell a joke",
        gerund="telling jokes",
        mess="laughter",
        risk="losing the beat",
        keyword="funny",
        tags={"humor", "comedy"},
    ),
    "juggle": Act(
        id="juggle",
        verb="juggle drumsticks",
        gerund="juggling drumsticks",
        mess="clatter",
        risk="dropping the sticks",
        keyword="sticks",
        tags={"band", "humor"},
    ),
    "dance": Act(
        id="dance",
        verb="dance in time",
        gerund="dancing in time",
        mess="laughter",
        risk="forgetting the count",
        keyword="dance",
        tags={"comedy", "band"},
    ),
    "drum": Act(
        id="drum",
        verb="play the drum solo",
        gerund="playing a drum solo",
        mess="noise",
        risk="rushing the beat",
        keyword="drum",
        tags={"band"},
    ),
}

GADGETS = [
    Gadget(
        id="metronome",
        label="a tiny metronome",
        phrase="a tiny metronome with a blinking light",
        helps={"noise", "laughter"},
        prep="set up a tiny metronome first",
        tail="set the metronome on the crate and counted along",
    ),
    Gadget(
        id="sunglasses",
        label="silly sunglasses",
        phrase="silly sunglasses with star-shaped frames",
        helps={"laughter"},
        prep="put on the silly sunglasses",
        tail="put on the silly sunglasses and grinned",
    ),
    Gadget(
        id="cowbell",
        label="a cowbell",
        phrase="a shiny cowbell",
        helps={"clatter", "noise"},
        prep="hang up a cowbell as a cue",
        tail="hung up the cowbell and tapped it once",
    ),
]

GIRL_NAMES = ["Mia", "Luna", "Piper", "Zoey", "Nora", "Tia", "Ivy", "Riley"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    activity: str
    name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTS[act_id]
            if any(act.mess in g.helps for g in GADGETS):
                combos.append((setting_id, act_id))
    return combos


def explain_rejection(setting_id: str, act_id: str) -> str:
    act = ACTS[act_id]
    return (
        f"(No story: {act.gerund} does not have a believable fix in {SETTINGS[setting_id].place}. "
        f"Try a different act or setting.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(S,A) :- affords(S,A), act(A), has_fix(A).
has_fix(A) :- act(A), mess_of(A,M), gadget(G), helps(G,M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTS.items():
        lines.append(asp.fact("act", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
    for g in GADGETS:
        lines.append(asp.fact("gadget", g.id))
        for m in sorted(g.helps):
            lines.append(asp.fact("helps", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
class SimWorld(World):
    pass


def choose_gadget(act: Act) -> Optional[Gadget]:
    for g in GADGETS:
        if act.mess in g.helps:
            return g
    return None


def tell(setting: Setting, act: Act, name: str) -> World:
    w = SimWorld(setting)
    girl = w.add(Entity(id=name, kind="character", type="girl"))
    band = w.add(Entity(id="band", kind="thing", type="band", label="the band", plural=True))

    tempo = 1.0
    focus = 1.0
    laughter = 0.0
    together = 1.0

    girl.memes.update(joy=1.0, humor=1.0, nerves=0.0)
    band.memes.update(focus=focus, together=together)

    w.say(f"{girl.id} loved the band, and {girl.pronoun()} was glad to play with everyone.")
    w.say(f"{girl.id} had a funny grin that made people wait for the punchline.")
    w.say(f"At {setting.place}, the band was getting ready for a small show.")

    w.para()
    w.say(f"{girl.id} wanted to {act.verb}, but the room was already buzzing.")
    girl.memes["nerves"] += 1.0
    girl.memes["humor"] += 1.0
    laughter += 1.0
    band.memes["focus"] -= 0.25

    if act.id == "joke":
        w.say(f"{girl.id} told a joke about a trumpet that could only say beep.")
        w.say(f"That made everyone laugh so hard that the count almost slipped away.")
        band.memes["focus"] -= 0.5
        together -= 0.25
    elif act.id == "juggle":
        w.say(f"{girl.id} tried to juggle drumsticks, and one stick pinged off a chair.")
        w.say(f"The band laughed, but the beat wobbled for a moment.")
        band.memes["focus"] -= 0.25
        together -= 0.25
    elif act.id == "dance":
        w.say(f"{girl.id} did a tiny dance step right on the count, and the drummer snorted.")
        w.say(f"The laughter was kind, but the band lost the first beat.")
        band.memes["focus"] -= 0.25
        together -= 0.2
    else:
        w.say(f"{girl.id} played a loud drum solo and accidentally rushed ahead.")
        w.say(f"The band blinked, then tried not to fall behind.")
        band.memes["focus"] -= 0.4
        together -= 0.1

    # Conflict / resolution
    w.para()
    if band.memes["focus"] < 1.0:
        w.say(f"The band looked at {girl.id}, and {girl.pronoun()} saw that the joke had gone a little too far.")
        w.say(f"{girl.id} took a breath and turned the funny part into the plan.")
        gadget = choose_gadget(act)
        if gadget:
            w.say(f"{girl.id} {gadget.prep}, then smiled and counted the band back in.")
            w.say(f"The room turned bright again when everyone laughed at the right moment.")
            girl.memes["joy"] += 1.0
            girl.memes["humor"] += 0.5
            band.memes["focus"] += 0.75
            band.memes["together"] += 0.5
            w.say(f"They {gadget.tail}, and the band found the beat together.")
        else:
            w.say(f"{girl.id} clapped twice and said, \"Again, but funnier!\"")
            band.memes["focus"] += 0.4
            w.say(f"This time, the band stayed with her and finished the song without wobbling.")
    else:
        w.say(f"The joke landed kindly, and the band kept smiling while they played.")

    w.para()
    if band.memes["together"] >= 1.0:
        w.say(f"In the end, {girl.id} was still laughing, and the band sounded even better because of it.")
    else:
        w.say(f"In the end, the band was a little messy, but {girl.id} made them laugh anyway.")

    w.facts.update(
        girl=girl,
        band=band,
        setting=setting,
        activity=act,
        gadget=choose_gadget(act),
    )
    return w


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    girl = f["girl"]
    act = f["activity"]
    return [
        f'Write a short comedy story for a child about a girl named {girl.id} and a band, using the word "{act.keyword}".',
        f"Tell a playful story where {girl.id} wants to {act.verb} but keeps making the band laugh.",
        f"Write a simple story about a girl, a band, and a funny moment that turns into a better performance.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    girl = f["girl"]
    act = f["activity"]
    setting = f["setting"]
    band = f["band"]
    gadget = f["gadget"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {girl.id}, a girl who loves being with the band at {setting.place}.",
        ),
        QAItem(
            question=f"What did {girl.id} want to do before the band started laughing?",
            answer=f"{girl.id} wanted to {act.verb}. That idea sounded funny enough to shake the band's focus for a moment.",
        ),
        QAItem(
            question=f"Why did the band have trouble at first?",
            answer=f"The band had trouble because {girl.id}'s funny moment made everyone laugh and almost lose the beat.",
        ),
    ]
    if gadget:
        qa.append(
            QAItem(
                question=f"How did {girl.id} help the band recover?",
                answer=f"{girl.id} used {gadget.label} to turn the joke into part of the plan, and then the band found the beat again.",
            )
        )
    qa.append(
        QAItem(
            question=f"What was the ending like?",
            answer=f"At the end, {girl.id} was still smiling and the band finished together, sounding better and happier.",
        )
    )
    return qa


WORLD_KNOWLEDGE = {
    "humor": [
        (
            "What is humor?",
            "Humor is something funny that makes people smile or laugh.",
        )
    ],
    "comedy": [
        (
            "What is comedy?",
            "Comedy is a kind of story, show, or joke that tries to be funny and make people laugh.",
        )
    ],
    "band": [
        (
            "What is a band?",
            "A band is a group of people who make music together.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.add("band")
    out: list[QAItem] = []
    for tag in ("humor", "comedy", "band"):
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE[tag])
    return out


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
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Storyworld: a girl, a band, and a comedy turn.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTS)
    ap.add_argument("--name", choices=GIRL_NAMES)
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
    combos = valid_combos()
    if args.setting and args.activity and (args.setting, args.activity) not in combos:
        raise StoryError(explain_rejection(args.setting, args.activity))
    valid = [
        c for c in combos
        if (args.setting is None or c[0] == args.setting)
        and (args.activity is None or c[1] == args.activity)
    ]
    if not valid:
        raise StoryError("(No valid combination matches the given options.)")
    setting_id, act_id = rng.choice(sorted(valid))
    name = args.name or rng.choice(GIRL_NAMES)
    return StoryParams(setting=setting_id, activity=act_id, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ACTS[params.activity], params.name)
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
    StoryParams(setting="gym", activity="joke", name="Mia"),
    StoryParams(setting="stage", activity="dance", name="Luna"),
    StoryParams(setting="garage", activity="juggle", name="Piper"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible (setting, activity) combos:\n")
        for c in combos:
            print(" ", c)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
