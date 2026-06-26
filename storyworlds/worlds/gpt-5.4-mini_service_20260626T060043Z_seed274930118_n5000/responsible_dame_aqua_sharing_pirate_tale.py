#!/usr/bin/env python3
"""
A small pirate-tale storyworld about a responsible dame, aqua, and sharing.

Seed tale:
---
A responsible dame pirate sailed out with a blue aqua cask on her ship.
The sea wind was hot, and the crew grew thirsty. One mate wanted to keep the
aqua all to herself, but the dame saw a better way. She shared the aqua by
pouring it into cups one by one, so everyone got a fair sip. The crew cheered,
and the cask lasted longer than anyone expected.

The simulated world tracks:
- physical meters: thirst, warmth, fullness, treasure, duty, spill
- emotional memes: pride, worry, fairness, greed, gratitude, calm

The story turns when the dame notices that sharing the aqua is the responsible
choice: it cools the crew, lowers conflict, and proves that fair care can feel
like treasure on a pirate ship.
"""

from __future__ import annotations

import argparse
import copy
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "dame"}
        male = {"boy", "man", "father", "pirate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    sea_state: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    effect: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    container: str
    plural: bool = False


@dataclass
class Aid:
    id: str
    label: str
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone

    def crew(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _apply_thirst(world: World) -> list[str]:
    out: list[str] = []
    for crew in world.crew():
        if crew.memes.get("thirsty", 0.0) < THRESHOLD:
            continue
        sig = ("thirst", crew.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        crew.meters["thirst"] = crew.meters.get("thirst", 0.0) + 1
        out.append(f"{crew.label} felt parched in the hot sea air.")
    return out


def _apply_share(world: World) -> list[str]:
    out: list[str] = []
    cask = world.entities.get("aqua_cask")
    if not cask or cask.meters.get("full", 0.0) < THRESHOLD:
        return out
    sharer = world.entities.get("dame")
    if not sharer:
        return out
    if sharer.memes.get("responsible", 0.0) < THRESHOLD:
        return out
    if world.facts.get("shared"):
        return out
    world.facts["shared"] = True
    for crew in world.crew():
        crew.meters["thirst"] = max(0.0, crew.meters.get("thirst", 0.0) - 1)
        crew.memes["gratitude"] = crew.memes.get("gratitude", 0.0) + 1
        crew.memes["calm"] = crew.memes.get("calm", 0.0) + 1
    cask.meters["full"] = max(0.0, cask.meters["full"] - 1)
    out.append("The dame shared the aqua so each sailor could have a fair sip.")
    return out


CAUSAL_RULES = [_apply_thirst, _apply_share]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sent = rule(world)
            if sent:
                changed = True
                out.extend(sent)
    if narrate:
        for s in out:
            world.say(s)
    return out


def build_story(world: World) -> None:
    dame = world.add(Entity(id="dame", kind="character", type="dame", label="the dame"))
    mate = world.add(Entity(id="mate", kind="character", type="pirate", label="the mate"))
    cask = world.add(Entity(
        id="aqua_cask",
        type="thing",
        label="aqua cask",
        phrase="a cool blue aqua cask",
    ))
    cups = world.add(Entity(
        id="cups",
        type="thing",
        label="little cups",
        phrase="little sharing cups",
        plural=True,
    ))
    world.facts.update(dame=dame, mate=mate, cask=cask, cups=cups)
    dame.memes["responsible"] = 1.0
    mate.memes["thirsty"] = 1.0
    cask.meters["full"] = 1.0

    world.say(
        "On the deck of the small pirate ship, a responsible dame kept watch over "
        "a cool blue aqua cask."
    )
    world.say(
        "The sun was bright, the sea wind was salty, and the crew had been sailing "
        "for a long while."
    )
    world.say(
        "The mate eyed the aqua and tried to keep it close, because the ship felt "
        "hot and the voyage felt long."
    )

    world.para()
    world.say(
        "The dame saw the thirsty faces, and she knew a fair choice would be the "
        "responsible one."
    )
    propagate(world, narrate=True)
    world.say(
        "She filled the little cups one by one, and the crew took only a small sip each."
    )

    world.para()
    if world.facts.get("shared"):
        world.say(
            "The mate stopped guarding the cask and smiled instead, because everyone "
            "got enough aqua to feel better."
        )
        world.say(
            "By sunset, the deck was calm again, and the blue cask was still there, "
            "proof that sharing had helped the whole ship."
        )
    else:
        world.say(
            "Nothing changed, but that would not be a proper pirate tale, so the dame "
            "chose the fair way anyway."
        )

    world.facts["resolved"] = True


SETTINGS = {
    "ship": Setting(place="the ship", sea_state="calm", affords={"sharing"}),
    "harbor": Setting(place="the harbor", sea_state="breezy", affords={"sharing"}),
    "island": Setting(place="the island beach", sea_state="hot", affords={"sharing"}),
}

ACTIONS = {
    "sharing": Action(
        id="sharing",
        verb="share the aqua",
        gerund="sharing aqua",
        rush="keep the aqua for herself",
        risk="the crew will stay thirsty",
        effect="everyone gets a fair sip",
        keyword="sharing",
        tags={"sharing", "aqua", "pirate"},
    ),
}

PRIZES = {
    "aqua": Prize(
        label="aqua",
        phrase="a cool blue aqua cask",
        type="cask",
        container="cask",
    ),
    "barrel": Prize(
        label="barrel",
        phrase="a heavy water barrel",
        type="barrel",
        container="barrel",
    ),
}

AIDS = {
    "cups": Aid(
        id="cups",
        label="little cups",
        prep="pour the aqua into little cups",
        tail="set the empty cups in a neat row",
    ),
    "ladle": Aid(
        id="ladle",
        label="a ladle",
        prep="scoop the aqua with a ladle",
        tail="hung the ladle back on its hook",
    ),
}

NAMES = ["Mara", "Nell", "Ivy", "Rhea", "Tamsin", "Ada"]
TRAITS = ["responsible", "brave", "steady", "kind", "patient"]


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    name: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for action in ACTIONS:
            for prize in PRIZES:
                if action in setting.affords and prize == "aqua":
                    combos.append((place, action, prize))
    return combos


def explain_rejection(action: Action, prize: Prize) -> str:
    return (
        f"(No story: this pirate world only supports {action.keyword} with the "
        f"shared aqua cask, because the tale depends on fair sharing and a real thirst problem.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.action and args.prize and (args.action != "sharing" or args.prize != "aqua"):
        raise StoryError(explain_rejection(ACTIONS[args.action], PRIZES[args.prize]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.action is None or c[1] == args.action)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid pirate sharing story matches those options.)")
    place, action, prize = rng.choice(combos)
    return StoryParams(
        place=place,
        action=action,
        prize=prize,
        name=args.name or rng.choice(NAMES),
        trait=args.trait or rng.choice(TRAITS),
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts
    return [
        'Write a short pirate tale for a young child about a responsible dame and a blue aqua cask.',
        f"Tell a gentle story where {p['name']} the dame chooses sharing over keeping the aqua to herself.",
        "Write a story with a clear beginning, a thirsty middle, and an ending where the crew feels fair and glad.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts
    return [
        QAItem(
            question=f"Who was the responsible dame in the story?",
            answer=f"The responsible dame was {p['name']}, who watched over the aqua cask on the ship.",
        ),
        QAItem(
            question="Why did the crew need the aqua?",
            answer="They had been sailing in hot sea air, so the crew was thirsty and needed a fair sip of water.",
        ),
        QAItem(
            question="What changed when the dame shared the aqua?",
            answer="The crew felt calmer and more grateful, and the cask lasted because everyone only took a small sip.",
        ),
        QAItem(
            question="What made the dame's choice responsible?",
            answer="She noticed the thirsty crew and chose to share the aqua fairly instead of letting one sailor keep it all.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use or enjoy something too, instead of keeping it all for yourself.",
        ),
        QAItem(
            question="Why is fresh water important on a ship?",
            answer="Fresh water helps sailors drink, stay healthy, and feel better when the weather is hot and salty.",
        ),
        QAItem(
            question="What is a cask?",
            answer="A cask is a strong barrel or container that can hold drinks like water.",
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A story is valid if the place affords sharing and the prize is the aqua cask.
valid(Place, Action, Prize) :- affords(Place, Action), action(Action), prize(Prize), prize_kind(Prize, aqua).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, act))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_kind", pid, prize.label))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld about a responsible dame and shared aqua.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--trait")
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


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    world.facts.update(name=params.name, trait=params.trait)
    build_story(world)
    return world


def generate(params: StoryParams) -> StorySample:
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


CURATED = [
    StoryParams(place="ship", action="sharing", prize="aqua", name="Mara", trait="responsible"),
    StoryParams(place="harbor", action="sharing", prize="aqua", name="Nell", trait="kind"),
    StoryParams(place="island", action="sharing", prize="aqua", name="Ivy", trait="steady"),
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
        print(f"{len(combos)} compatible story combos:\n")
        for combo in combos:
            print(" ", combo)
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
