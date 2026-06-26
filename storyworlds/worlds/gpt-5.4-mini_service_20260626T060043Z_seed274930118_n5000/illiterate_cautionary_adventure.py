#!/usr/bin/env python3
"""
A small cautionary adventure world about an illiterate child who wants to
explore, but must learn to listen, ask for help, and stay safe.

The story premise:
- A brave child loves adventure.
- They cannot read important signs, labels, or maps.
- A risky path or object tempts them.
- A careful helper warns them, and they choose a safer route.

This world is intentionally tiny and constraint-checked: the central danger is
real only when the hero cannot read a warning, and the resolution always comes
from a safer method rather than from ignoring the caution.
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
# Data model
# ---------------------------------------------------------------------------
@dataclass
class Character:
    name: str
    role: str
    adjective: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.role in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.role in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    terrain: str
    hazard: str
    has_signs: bool = True


@dataclass
class Quest:
    goal: str
    verb: str
    risky_thing: str
    warning: str
    safer_choice: str
    success_image: str
    danger_meter: str
    caution_meter: str
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    quest: str
    hero_name: str
    hero_role: str
    companion_role: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting, quest: Quest, hero: Character, companion: Character):
        self.setting = setting
        self.quest = quest
        self.hero = hero
        self.companion = companion
        self.events: list[str] = []
        self.facts: dict[str, object] = {}
        self.trace: list[str] = []

    def say(self, text: str) -> None:
        self.events.append(text)

    def add_trace(self, text: str) -> None:
        self.trace.append(text)

    def render(self) -> str:
        return " ".join(self.events)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
SETTINGS = {
    "forest": Setting(place="the forest edge", terrain="trees and roots", hazard="a narrow ravine"),
    "cave": Setting(place="the cave mouth", terrain="stone and echoes", hazard="a deep dark tunnel"),
    "harbor": Setting(place="the harbor dock", terrain="planks and ropes", hazard="a slippery jetty"),
    "hill": Setting(place="the windy hill", terrain="grass and rocks", hazard="a steep drop"),
}

QUESTS = {
    "trail": Quest(
        goal="find the hidden trail",
        verb="follow the trail",
        risky_thing="a sign that says KEEP OUT",
        warning="The sign warned that the path was too steep and crumbly",
        safer_choice="ask a grown-up to read the sign and choose the marked path",
        success_image="the child walked the marked path with steady feet and a bright pack",
        danger_meter="drop",
        caution_meter="care",
        clue="sign",
        tags={"forest", "sign", "trail"},
    ),
    "boat": Quest(
        goal="reach the little boat",
        verb="walk to the boat",
        risky_thing="a note tied to the dock post",
        warning="The note warned that the boards were slick and a wave could knock a child down",
        safer_choice="wait for help and use the handrail instead of rushing ahead",
        success_image="the child crossed safely while the boat bobbed softly beside the dock",
        danger_meter="slip",
        caution_meter="patience",
        clue="dock",
        tags={"harbor", "dock", "water"},
    ),
    "tunnel": Quest(
        goal="see what was inside the tunnel",
        verb="go into the tunnel",
        risky_thing="a wooden board painted with red words",
        warning="The board warned that the tunnel had loose stones and no light",
        safer_choice="take a lantern and go with a helper who could read the board",
        success_image="the lantern shone on safe stones while the helper led the way",
        danger_meter="fall",
        caution_meter="light",
        clue="board",
        tags={"cave", "light", "stone"},
    ),
    "ridge": Quest(
        goal="reach the high ridge",
        verb="climb the ridge",
        risky_thing="a rope fence with a bright warning tag",
        warning="The tag warned that the edge was windy and the rocks could shift",
        safer_choice="stay behind the fence and take the safer lookout trail",
        success_image="the child looked out from the lookout trail and watched clouds float by",
        danger_meter="fall",
        caution_meter="care",
        clue="ridge",
        tags={"hill", "wind", "rope"},
    ),
}


TRAITS = ["brave", "curious", "lively", "quick", "spirited", "bold"]
GIRL_NAMES = ["Mina", "Tia", "Luna", "Rosa", "Nia", "Ava", "Maya", "Iris"]
BOY_NAMES = ["Tobin", "Evan", "Milo", "Jace", "Leo", "Nico", "Tariq", "Owen"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A quest is dangerous if the setting contains the hazard and the hero cannot read the warning.
dangerous(S,Q) :- setting(S), quest(Q), hazard(S,H), risk(Q,H), illiterate(hero).

% A safe ending requires the helper's caution and the safer choice.
safe(S,Q) :- setting(S), quest(Q), caution(Q), safer(Q).

#show dangerous/2.
#show safe/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place", sid, s.place))
        lines.append(asp.fact("terrain", sid, s.terrain))
        lines.append(asp.fact("hazard", sid, s.hazard))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("goal", qid, q.goal))
        lines.append(asp.fact("risk", qid, q.clue))
        lines.append(asp.fact("caution", qid))
        lines.append(asp.fact("safer", qid))
    lines.append(asp.fact("illiterate", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show dangerous/2.\n#show safe/2."))
    atoms = set((a[0], a[1]) for a in asp.atoms(model, "dangerous"))
    expected = {(sid, qid) for sid in SETTINGS for qid in QUESTS}
    if atoms != expected:
        print("MISMATCH in ASP dangerous/2 facts")
        print("ASP:", sorted(atoms))
        print("PY :", sorted(expected))
        return 1
    print(f"OK: ASP parity check passed ({len(atoms)} dangerous pairs).")
    return 0


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def select_valid_combo(rng: random.Random, args: argparse.Namespace) -> tuple[str, str]:
    combos = []
    for sid, s in SETTINGS.items():
        if args.setting and args.setting != sid:
            continue
        for qid, q in QUESTS.items():
            if args.quest and args.quest != qid:
                continue
            if sid in q.tags:
                combos.append((sid, qid))
    if not combos:
        raise StoryError("No valid setting/quest combination matches the given options.")
    return rng.choice(sorted(combos))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small cautionary adventure world about an illiterate explorer."
    )
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--quest", choices=sorted(QUESTS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion", choices=["mother", "father", "guide"])
    ap.add_argument("--trait", choices=TRAITS)
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
    setting, quest = select_valid_combo(rng, args)

    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    companion = args.companion or rng.choice(["mother", "father", "guide"])
    trait = args.trait or rng.choice(TRAITS)

    return StoryParams(
        setting=setting,
        quest=quest,
        hero_name=name,
        hero_role=gender,
        companion_role=companion,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    quest = QUESTS[params.quest]
    hero = Character(
        name=params.hero_name,
        role=params.hero_role,
        adjective=params.trait,
        meters={"distance": 0.0, quest.danger_meter: 0.0, "safety": 0.0},
        memes={"curiosity": 1.0, "caution": 0.0, "relief": 0.0, "worry": 0.0},
    )
    companion = Character(
        name={"mother": "Mom", "father": "Dad", "guide": "the guide"}[params.companion_role],
        role=params.companion_role,
        adjective="careful",
        meters={"distance": 0.0, "safety": 0.0},
        memes={"worry": 1.0, "care": 1.0},
    )

    world = World(setting, quest, hero, companion)
    world.facts.update(params=params, setting=setting, quest=quest, hero=hero, companion=companion)

    # Act 1: setup.
    world.say(
        f"{hero.name} was a {hero.adjective} little {hero.role} who loved adventure, "
        f"especially near {setting.place}."
    )
    world.say(
        f"{hero.name} wanted to {quest.verb} because {hero.pronoun('subject')} thought "
        f"{quest.goal} would be exciting."
    )
    world.say(
        f"But {hero.name} could not read {quest.risky_thing}, and that made the path tricky."
    )

    # Act 2: warning and tension.
    world.say(
        f"At the edge of {setting.place}, {companion.name} pointed to the warning and said, "
        f"\"{quest.warning}.\""
    )
    hero.memes["worry"] += 1.0
    hero.memes["caution"] += 1.0
    world.say(
        f"{hero.name} leaned closer, wishing {hero.pronoun('subject')} could read the words "
        f"by {hero.pronoun('possessive')}self."
    )
    world.say(
        f"For a moment, {hero.name} felt the pull of the risky way forward."
    )
    hero.meters["distance"] += 1.0
    world.facts["danger_seen"] = True

    # Act 3: turn and resolution.
    world.say(
        f"Then {hero.name} stopped and listened."
    )
    world.say(
        f"{companion.name} offered a better plan: {quest.safer_choice}."
    )
    hero.meters["safety"] += 1.0
    hero.memes["relief"] += 1.0
    hero.memes["worry"] = 0.0
    world.say(
        f"{hero.name} nodded, stayed on the safe side, and chose the careful way."
    )
    world.say(
        f"In the end, {quest.success_image}."
    )

    world.facts["resolved"] = True
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    q: Quest = world.facts["quest"]
    s: Setting = world.facts["setting"]
    return [
        f"Write a cautionary adventure story about {p.hero_name} at {s.place} who cannot read {q.risky_thing}.",
        f"Tell a short adventurous tale where a {p.hero_role} named {p.hero_name} must choose the safe path instead of {q.verb}.",
        f"Write a child-friendly story that includes an unread warning, a helpful companion, and a safer choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    q: Quest = world.facts["quest"]
    s: Setting = world.facts["setting"]
    h: Character = world.facts["hero"]
    c: Character = world.facts["companion"]

    return [
        QAItem(
            question=f"Why was {p.hero_name} in danger near {s.place}?",
            answer=(
                f"{p.hero_name} was in danger because {h.pronoun('subject')} could not read "
                f"{q.risky_thing}, and the warning said the place was unsafe."
            ),
        ),
        QAItem(
            question=f"What did {c.name} want {p.hero_name} to do instead of {q.verb}?",
            answer=f"{c.name} wanted {p.hero_name} to {q.safer_choice}.",
        ),
        QAItem(
            question=f"How did the story end for {p.hero_name}?",
            answer=(
                f"{p.hero_name} chose the careful path, listened to {c.name}, and stayed safe."
            ),
        ),
        QAItem(
            question=f"Why is this an adventure story and not just an ordinary walk?",
            answer=(
                f"It is an adventure story because {p.hero_name} wanted to explore a risky place, "
                f"had to face a warning, and made a brave choice to keep going safely."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    q: Quest = world.facts["quest"]
    s: Setting = world.facts["setting"]
    out = [
        QAItem(
            question="What does it mean to be illiterate?",
            answer="Being illiterate means a person cannot read written words yet.",
        ),
        QAItem(
            question="Why should someone listen to a warning sign?",
            answer="A warning sign can help keep people safe by telling them about danger before they go too far.",
        ),
        QAItem(
            question="What is a safer choice when a path is risky?",
            answer="A safer choice is to slow down, ask for help, and pick a route that avoids the danger.",
        ),
    ]
    if "sign" in q.tags or "board" in q.tags:
        out.append(
            QAItem(
                question="What is a sign for?",
                answer="A sign gives information or warning so people know where to go and what to avoid.",
            )
        )
    if "water" in q.tags:
        out.append(
            QAItem(
                question="Why can dock boards be slippery?",
                answer="Dock boards can get slippery because water makes the wood wet and smooth.",
            )
        )
    if "stone" in q.tags:
        out.append(
            QAItem(
                question="Why do cave explorers carry lanterns?",
                answer="Lanterns help explorers see the path when a cave is dark.",
            )
        )
    if "wind" in q.tags:
        out.append(
            QAItem(
                question="Why can a windy ridge be dangerous?",
                answer="Strong wind can push people off balance, especially near a steep edge.",
            )
        )
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"setting={world.setting}")
    lines.append(f"quest={world.quest}")
    lines.append(f"hero.meters={world.hero.meters}")
    lines.append(f"hero.memes={world.hero.memes}")
    lines.append(f"companion.memes={world.companion.memes}")
    lines.append("events:")
    for e in world.trace:
        lines.append(f"  {e}")
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


def curated() -> list[StoryParams]:
    return [
        StoryParams(setting="forest", quest="trail", hero_name="Mina", hero_role="girl", companion_role="mother", trait="brave"),
        StoryParams(setting="harbor", quest="boat", hero_name="Owen", hero_role="boy", companion_role="father", trait="curious"),
        StoryParams(setting="cave", quest="tunnel", hero_name="Luna", hero_role="girl", companion_role="guide", trait="bold"),
        StoryParams(setting="hill", quest="ridge", hero_name="Tobin", hero_role="boy", companion_role="mother", trait="spirited"),
    ]


def asp_valid_pairs() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show dangerous/2.\n#show safe/2."))
    return sorted(set(asp.atoms(model, "dangerous")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show dangerous/2.\n#show safe/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show dangerous/2.\n#show safe/2."))
        print("dangerous pairs:", sorted(set(asp.atoms(model, "dangerous"))))
        print("safe pairs:", sorted(set(asp.atoms(model, "safe"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in curated()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
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
            header = f"### {p.hero_name}: {p.setting}/{p.quest}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    q: Quest = world.facts["quest"]
    s: Setting = world.facts["setting"]
    c: Character = world.facts["companion"]
    return [
        QAItem(
            question=f"Why did {p.hero_name} need help at {s.place}?",
            answer=(
                f"{p.hero_name} needed help because {h_pronoun(p.hero_role)} could not read "
                f"{q.risky_thing}, so the warning could not be understood alone."
            ),
        ),
        QAItem(
            question=f"What safer choice did {c.name} offer?",
            answer=f"{c.name} offered the safer choice to {q.safer_choice}.",
        ),
        QAItem(
            question=f"What was the important caution in this story?",
            answer=(
                f"The important caution was that a warning at {s.place} should be listened to, "
                f"especially when someone is illiterate and cannot read it."
            ),
        ),
        QAItem(
            question=f"What changed by the end of the adventure?",
            answer=(
                f"By the end, {p.hero_name} chose caution over rushing ahead, and the adventure ended safely."
            ),
        ),
    ]


def h_pronoun(role: str) -> str:
    return {"girl": "she", "boy": "he"}.get(role, "they")


def world_knowledge_qa(world: World) -> list[QAItem]:
    q: Quest = world.facts["quest"]
    out = [
        QAItem(
            question="What does a cautionary story try to do?",
            answer="A cautionary story tries to warn the reader about a mistake and show a safer choice.",
        ),
        QAItem(
            question="Why are rules near dangerous places important?",
            answer="Rules help keep explorers safe when cliffs, water, dark tunnels, or slippery boards are nearby.",
        ),
    ]
    if q.clue in {"sign", "board"}:
        out.append(QAItem(
            question="Why are written warnings useful?",
            answer="Written warnings tell people about danger before they step into it.",
        ))
    return out


if __name__ == "__main__":
    main()
